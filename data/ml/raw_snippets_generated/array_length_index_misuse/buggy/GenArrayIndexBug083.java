public class GenArrayIndexBug083 {
    static void stampLast(int[] prices, int value) {
        prices[prices.length] = value;
    }
}
