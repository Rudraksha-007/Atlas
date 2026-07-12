import api from "./api";

export interface SignupPayload {
  user_name: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export const signup = async (data: SignupPayload) => {
  const response = await api.post("/local/signup", data);
  return response.data;
};

export const login = async (data: LoginPayload) => {
  const response = await api.post("/local/login", data);

  return response.data;
};

export const logout = async (refresh_token: string) => {
  const response = await api.post("/logout", {
    refresh_token,
  });

  return response.data;
};

export const refresh = async (
  access_token: string,
  refresh_token: string
) => {
  const response = await api.post("/refresh", {
    access_token,
    refresh_token,
  });

  return response.data;
};