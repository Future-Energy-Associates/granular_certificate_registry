import React from "react";
import { Card, Col, Divider } from "antd";
import { useAccount } from "../../context/AccountContext";
import certificateTotal from "../../assets/images/certificate-total.png";
import certificateTransferred from "../../assets/images/certificate-transferred.png";
import certificateCancelled from "../../assets/images/certificate-cancelled.png";
import * as styles from "./Certificate.module.css";
import { DEVICE_TECHNOLOGY_TYPE } from "../../enum";

const Summary = () => {
  const { currentAccount } = useAccount();

    // Get top 3 devices with the highest quantity in summary
    // Convert object to array of [key, value] pairs, sort by value, and get top 3
    const topThreeDevices = Object.entries(
      currentAccount?.summary.num_devices_by_type || {}
    )
      .sort((a, b) => b[1] - a[1]) // Sort by value (second element of the array)
      .slice(0, 3) // Get the top 3
      .map(([type, count]) => ({ type, count })); // Convert back to an array of object
      
  return (
    <>
      {" "}
      <Col span={12}>
        <Card className={styles["card-wrapper"]}>
          <div className={styles["card-body"]}>
            <img className={styles["icon-img"]} src={certificateTotal} />
            <div className={styles["information-container"]}>
              <h3 className={styles["summary-value"]}>
                {currentAccount?.summary.num_granular_certificate_bundles ||
                  "0"}
              </h3>
              <p className={styles["summary-text"]}>Total Certificates</p>
            </div>
            <Divider
              type="vertical"
              style={{ height: "50px", margin: "0", color: "#DADCE0" }}
            />
            {topThreeDevices.map((deviceQuantity, index) => (
              <div className={styles["top-device-container"]} key={index}>
                <h3 className={styles["summary-value"]}>
                  {deviceQuantity.count || "0"}
                </h3>
                <p className={styles["summary-text"]}>
                  {DEVICE_TECHNOLOGY_TYPE[deviceQuantity.type.toUpperCase()]}
                </p>
              </div>
            ))}
          </div>
        </Card>
      </Col>
      <Col span={6}>
        <Card className={styles["card-wrapper"]}>
          <div className={styles["card-body"]}>
            <img className={styles["icon-img"]} src={certificateTransferred} />
            <div className={styles["information-container"]}>
              <h3 className={styles["summary-value"]}>
                {Math.floor(
                  currentAccount?.summary.num_granular_certificate_bundles *
                    0.25
                ) || "0"}
              </h3>
              <p className={styles["summary-text"]}>Certificates Transferred</p>
            </div>
          </div>
        </Card>
      </Col>
      <Col span={6}>
        <Card className={styles["card-wrapper"]}>
          <div className={styles["card-body"]}>
            <img className={styles["icon-img"]} src={certificateCancelled} />
            <div className={styles["information-container"]}>
              <h3 className={styles["summary-value"]}>
                {currentAccount?.summary
                  .num_cancelled_granular_certificate_bundles || "0"}
              </h3>
              <p className={styles["summary-text"]}>Certificates Cancelled</p>
            </div>
          </div>
        </Card>
      </Col>
    </>
  );
};

export default Summary;
