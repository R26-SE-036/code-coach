public class GenOffByOneBug100 {
    static int sum1(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }

    static void show(int[] prices) {
        for (int i = 0; i <= prices.length; i++) {
            System.out.println(prices[i]);
        }
    }
}
