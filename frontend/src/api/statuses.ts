import { get } from "./client";
import type { Status } from "../types";

export const listStatuses = () => get<Status[]>("/statuses");
