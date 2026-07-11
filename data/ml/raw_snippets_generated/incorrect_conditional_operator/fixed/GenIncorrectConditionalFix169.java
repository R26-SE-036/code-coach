public class GenIncorrectConditionalFix169 {
    static void announce(int budget) {
        if (budget == 10) {
            System.out.println("hit the target");
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

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static boolean isEven3(int count) {
        return count % 2 == 0;
    }

    static void printAll4(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static int sum5(int[] weights) {
        int total = 0;
        for (int i = 0; i < weights.length; i++) {
            total += weights[i];
        }
        return total;
    }
}
