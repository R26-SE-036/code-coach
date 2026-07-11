public class GenOffByOneBug099 {
    static void show(int[] prices) {
        for (int i = 0; i <= prices.length; i++) {
            System.out.println(prices[i]);
        }
    }

    static void printAll1(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }
}
