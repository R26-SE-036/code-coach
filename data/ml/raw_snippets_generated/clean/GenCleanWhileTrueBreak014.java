public class GenCleanWhileTrueBreak014 {
    static boolean isEven1(int level) {
        return level % 2 == 0;
    }

    static int largest2(int[] prices) {
        int best = prices[0];
        for (int i = 1; i < prices.length; i++) {
            if (prices[i] > best) {
                best = prices[i];
            }
        }
        return best;
    }

    static int drain3(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }

    static void printAll4(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }

    static int spin(int total) {
        int rounds = 0;
        while (true) {
            rounds++;
            if (rounds > total) {
                break;
            }
        }
        return rounds;
    }
}
