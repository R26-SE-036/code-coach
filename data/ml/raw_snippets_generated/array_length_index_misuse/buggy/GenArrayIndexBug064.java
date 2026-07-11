public class GenArrayIndexBug064 {
    static void showLast(int[] prices) {
        System.out.println(prices[prices.length]);
    }

    static boolean isEven1(int budget) {
        return budget % 2 == 0;
    }
}
