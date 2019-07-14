import { Transcript } from "../types";

export interface ResultBlock<T> {
  result: T;
  isOpen: boolean;
  onClick: () => any;
  transcript: Transcript;
}
