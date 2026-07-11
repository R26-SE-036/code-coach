public class GenOffByOneFix021 {
    static int drain1(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }

    static void show(int[] prices) {
        for (int i = 0; i < prices.length; i++) {
            System.out.println(prices[i]);
        }
    }
}
