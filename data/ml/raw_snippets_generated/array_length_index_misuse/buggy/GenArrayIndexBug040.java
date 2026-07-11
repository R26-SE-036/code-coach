public class GenArrayIndexBug040 {
    static void stampLast(int[] stocks, int value) {
        stocks[stocks.length] = value;
    }
}
