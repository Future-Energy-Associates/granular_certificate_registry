import importlib
import os
from typing import List, Literal, Optional

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy_utils import create_database, database_exists
from sqlmodel import Session, SQLModel, create_engine, select
from tqdm import tqdm

# Loading environment variables

load_dotenv()
DB_USER = os.environ['DB_USER']
DB_PSWD = os.environ['DB_PSWD']
DB_URL = os.environ['DB_URL']
DB_PORT = os.environ['DB_PORT']
DB_TEST_FP = os.environ['DB_TEST_FP']
ENVIRONMENT = os.environ['ENVIRONMENT']


# Defining utility functions and classes

def schema_path_to_class(schema_path):
    *module_path, schema_class_name = schema_path.split('.')
    schema_class = getattr(importlib.import_module('.'.join(module_path)), schema_class_name)

    return schema_class


def df_to_records_without_nulls(df):
    records = [
        {
            k: v
            for k, v
            in record.items()
            if v is not None
        }
        for record
        in df.replace(np.nan, None).to_dict('records')
    ]

    return records


class DButils:
    def __init__(
            self,
            db_username: Optional[str] = None,
            db_password: Optional[str] = None,
            db_url: Optional[str] = None,
            db_port: Optional[int] = None,
            db_name: Optional[str] = None,
            db_test_fp: Optional[str] = None
    ):
        self._db_username = db_username
        self._db_password = db_password
        self._db_url = db_url
        self._db_port = db_port
        self._db_name = db_name
        self._db_test_fp = db_test_fp

        if ENVIRONMENT == 'PROD':
            self.connection_str = f'postgresql://{self._db_username}:{self._db_password}@{self._db_url}:' \
                                  f'{self._db_port}/{self._db_name}'
        elif ENVIRONMENT == 'STAGE':
            self.connection_str = f'sqlite:///{self._db_test_fp}'
        else:
            raise ValueError('`ENVIRONMENT` must be one of: `PROD` or `STAGE`')

        self.engine = create_engine(self.connection_str, pool_pre_ping=True)

    def yield_session(self):
        with Session(self.engine) as session:
            yield session

    def load_table_as_df(
            self,
            schema_path='dbutils.schemas.messages.MessageMetadata',
            use_pandas=False,
            pd_select_statement: str = 'SELECT *',
            offset: int = 0,
            limit: int = 500,
            sort_col: Optional[str] = None,
            sort_dir: Optional[Literal['asc', 'desc']] = None,
            dt_col: Optional[str] = None  # assumed to be a unix timestamp
    ):
        if use_pandas:
            table_name = schema_path.split('.')[-1].lower()
            df = pd.read_sql(sql=f'{pd_select_statement} FROM {table_name};', con=self.connection_str)

        else:
            schema_class = schema_path_to_class(schema_path)
            select_statement = select(schema_class)

            if sort_col is not None:
                if sort_dir is not None:
                    select_statement = select_statement.order_by(getattr(getattr(schema_class, sort_col), sort_dir)())
                else:
                    select_statement = select_statement.order_by(getattr(schema_class, sort_col))

            with Session(self.engine) as session:
                results = session.exec(
                    select_statement
                    .offset(offset)
                    .limit(limit)
                ).all()

            df = pd.DataFrame.from_records([
                schema_class.from_orm(elem).dict()
                for elem
                in results
            ])

        if dt_col is not None:
            assert dt_col in df.columns, f'{dt_col} is not one of the columns contained within the table'
            df[dt_col] = pd.to_datetime(df[dt_col], unit='s')

        return df

    def get_table_row(self, col_name: str, value: str, schema_path: str):
        schema_class = schema_path_to_class(schema_path)

        with Session(self.engine) as session:
            statement = select(schema_class).where(getattr(schema_class, col_name) == value)
            results = session.exec(statement)
            result = results.first()  # should assert there's only one

        return result

    def initiate_db_tables(
            self,
            schema_paths: list = None
    ) -> None:
        if schema_paths is None:
            schema_paths = []
        if not database_exists(self.engine.url):
            create_database(self.engine.url)

        if len(schema_paths) > 0:
            tables = [schema_path_to_class(schema_path).__table__ for schema_path in schema_paths]
        else:
            tables = None

        SQLModel.metadata.create_all(self.engine, tables=tables)

        return None

    def save_rows(self, schema_path: str, rows: List[dict]):
        with Session(self.engine) as session:
            schema_class = schema_path_to_class(schema_path)

            for single_row_data in tqdm(rows, desc='saving rows'):
                row_entry = schema_class(**single_row_data)
                session.add(row_entry)

            session.commit()

    def save_dfs(self, schema_path_to_df_fp: dict):
        with Session(self.engine) as session:
            for schema_path, df_fp in schema_path_to_df_fp.items():
                if isinstance(df_fp, str):
                    df = pd.read_csv(df_fp)
                elif isinstance(df_fp, pd.DataFrame):
                    df = df_fp
                else:
                    raise ValueError(
                        'The values within the `schema_to_df_fp` object must be strings representing the filepaths to '
                        'CSVs or Pandas DataFrame objects')

                if isinstance(schema_path, str):
                    schema = schema_path_to_class(schema_path)
                else:
                    raise ValueError('Expected `schema_path` to be a string')

                for row_data in tqdm(df_to_records_without_nulls(df),
                                     desc=schema_path.split('.')[-1]):
                    try:
                        row_obj = schema(**row_data)
                        session.add(row_obj)
                    except:
                        pp_row_data = '\n'.join([f'{k}: {v}' for k, v in row_data.items()])
                        raise ValueError(f'Failed to process {schema_path} for entry:\n{pp_row_data}')

            session.commit()


# initialising all the DButil clients

db_names = ['authentication', 'production']

db_name_to_client = {
    db_name: DButils(
        db_username=DB_USER,
        db_password=DB_PSWD,
        db_url=DB_URL,
        db_port=int(DB_PORT),
        db_test_fp=DB_TEST_FP,
        db_name=db_name
    )
    for db_name
    in db_names
}
