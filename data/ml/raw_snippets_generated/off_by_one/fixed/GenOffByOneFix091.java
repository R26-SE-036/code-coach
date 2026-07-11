public class GenOffByOneFix091 {
    static int addUp(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }

    static String describe1(int limit) {
        if (limit < 100) {
            return "low";
        } else if (limit > 500) {
            return "high";
        }
        return "medium";
    }

    static boolean isEven2(int steps) {
        return steps % 2 == 0;
    }
}
