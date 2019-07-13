export interface ResultBlock<T> {
  result: T;
  isOpen: boolean;
  onClick: () => any;
}
