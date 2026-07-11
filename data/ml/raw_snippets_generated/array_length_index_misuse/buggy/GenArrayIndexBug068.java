public class GenArrayIndexBug068 {
    static void stampLast(int[] stocks, int value) {
        stocks[stocks.length] = value;
    }
}
