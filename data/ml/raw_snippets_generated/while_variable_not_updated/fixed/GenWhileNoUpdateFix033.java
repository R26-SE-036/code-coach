public class GenWhileNoUpdateFix033 {
    static int largest1(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void pump(boolean running, int points) {
        while (!running) {
            System.out.println(points);
            points++;
            running = points > 10;
        }
    }

    static int largest3(int[] weights) {
        int best = weights[0];
        for (int i = 1; i < weights.length; i++) {
            if (weights[i] > best) {
                best = weights[i];
            }
        }
        return best;
    }

    static void printAll4(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }
}
