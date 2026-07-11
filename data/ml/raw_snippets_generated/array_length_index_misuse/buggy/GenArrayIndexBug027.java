public class GenArrayIndexBug027 {
    static void stampLast(int[] prices, int value) {
        prices[prices.length] = value;
    }
}
