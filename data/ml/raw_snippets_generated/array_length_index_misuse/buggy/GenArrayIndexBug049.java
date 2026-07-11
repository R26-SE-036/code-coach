public class GenArrayIndexBug049 {
    static boolean isEven1(int stock) {
        return stock % 2 == 0;
    }

    static void showLast(int[] prices) {
        System.out.println(prices[prices.length]);
    }
}
