public class GenOffByOneFix085 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void show(int[] stocks) {
        for (int i = 0; i < stocks.length; i++) {
            System.out.println(stocks[i]);
        }
    }

    static int sum2(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }
}
