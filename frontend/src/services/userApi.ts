import axios from "axios";

export interface User {
  id: string;
  name: string;
  email: string;
  favorite_etfs: string[];
}

const client = axios.create({
  baseURL: "/api/v1",
});

export async function fetchUsers(): Promise<User[]> {
  const { data } = await client.get("/users/");
  return data;
}
