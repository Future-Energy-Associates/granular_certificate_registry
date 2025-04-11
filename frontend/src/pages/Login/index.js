import React, { useState } from "react";
import {
  Layout,
  Input,
  Button,
  Select,
  Typography,
  Divider,
  message,
} from "antd";
import * as styles from "./Login.module.css";
import pepLogo from "../../assets/images/pep-logo.png";
import googleLogo from "../../assets/images/google-logo.png";
import energyTagLogo from "../../assets/images/energy-tag-logo.png";

const { Content } = Layout;
const { Title, Text, Link } = Typography;
const { Option } = Select;

import { useDispatch } from "react-redux";
import { login } from "../../store/auth/authThunk";
import { readCurrentUser } from "../../store/user/userThunk";

import { useNavigate } from "react-router-dom";
import { useUser } from "../../context/UserContext";

const Login = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { saveUserData } = useUser();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await dispatch(login({ username, password })).unwrap();
      const userData = await dispatch(readCurrentUser()).unwrap();
      saveUserData(userData);
      message.success("Login successful 🎉", 2);
      navigate("/account-picker");
    } catch (error) {
      message.error(`Login failed: ${error}`, 3);
    }
  };
  return (
    <Layout>
      <Content className={styles["login-container"]}>
        <div className={styles["login-left"]}>
          <div
            style={{ maxWidth: 720, margin: "50px auto", textAlign: "center" }}
          >
            <Title className={styles["font-color"]} level={3}>
              Login to Account
            </Title>
            <Text type="secondary" style={{ marginTop: 12, color: "#5F6368" }}>
              Please enter your email and password to continue
            </Text>

            <div
              style={{
                marginTop: 16,
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
              }}
            >
              {/* Email Field */}
              <div style={{ marginTop: 16, width: "400px" }}>
                <div
                  className={`${styles["login-form-title"]} ${styles["font-color"]}`}
                >
                  <Text>Email</Text>
                </div>
                <Input
                  placeholder="Email"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  style={{ height: "40px" }}
                />
              </div>
              {/* Password Field */}
              <div style={{ marginTop: 16, width: "400px" }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                  }}
                  className={`${styles["login-form-title"]} ${styles["font-color"]}`}
                >
                  <Text>Password</Text>

                  <Link
                    href="https://docs.google.com/forms/d/e/1FAIpQLSdSkHMAYSu43VJFevngfVT5hvnWRZvwkelIf9QaPtpLVrIlxA/viewform?usp=sf_link"
                    style={{ color: "#202224" }}
                  >
                    Forgot password
                  </Link>
                </div>
                <Input.Password
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{ height: "40px" }}
                />
              </div>

              {/* Login Button */}
              <Button
                type="primary"
                onClick={handleSubmit}
                style={{
                  backgroundColor: "#1D53F7",
                  fontWeight: "500",
                  width: "400px",
                  height: "40px",
                  marginTop: 32,
                }}
                block
              >
                Login
              </Button>

              <div
                style={{ marginTop: 16, textAlign: "center", width: "400px" }}
              >
                <Divider
                  plain
                  style={{
                    marginBottom: 12,
                    borderColor: "#DADCE0",
                    color: "#5F6368",
                  }}
                >
                  Don’t have an account?
                </Divider>
                <Text>
                  <Link
                    href="https://docs.google.com/forms/d/e/1FAIpQLSdSkHMAYSu43VJFevngfVT5hvnWRZvwkelIf9QaPtpLVrIlxA/viewform?usp=sf_link"
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ fontWeight: "500", color: "#043DDC" }}
                  >
                    Request account
                  </Link>
                </Text>
              </div>

              <div style={{ marginTop: 64, color: "#5F6368" }}>
                <Text>Sponsored by:</Text>
              </div>

              <div className={styles["sponsors"]}>
                <img src={pepLogo} alt="Private Energy Partners" />
                <img src={googleLogo} alt="Google" />
                <img src={energyTagLogo} alt="Energy tag" />
              </div>
            </div>
          </div>
        </div>
        <div className={styles["login-right"]}>
          <Text
            style={{
              fontWeight: "500",
              position: "absolute",
              top: "32px",
              right: "83px",
              color: "#fff",
              fontSize: "30px",
              fontFamily: "Outfit",
            }}
          >
            Granular
          </Text>
          <Text
            style={{
              fontWeight: "500",
              position: "absolute",
              top: "64px",
              right: "83px",
              color: "#fff",
              fontSize: "30px",
              fontFamily: "Outfit",
            }}
          >
            Cert
          </Text>
          <Text
            style={{
              fontWeight: "900",
              position: "absolute",
              top: "64px",
              right: "40px",
              color: "#fff",
              fontSize: "30px",
              fontFamily: "Outfit",
            }}
          >
            OS
          </Text>
        </div>
      </Content>
    </Layout>
  );
};

export default Login;
