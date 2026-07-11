public class GenWhileNoUpdateBug112 {
    static void countdown(int level) {
        while (level > 0) {
            System.out.println("left: " + level);
        }
    }

    static int largest1(int[] prices) {
        int best = prices[0];
        for (int i = 1; i < prices.length; i++) {
            if (prices[i] > best) {
                best = prices[i];
            }
        }
        return best;
    }

    static void printAll2(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }
}
