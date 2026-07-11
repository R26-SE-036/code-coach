public class GenIncorrectConditionalFix146 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static boolean isEven2(int steps) {
        return steps % 2 == 0;
    }

    static int largest3(int[] scores) {
        int best = scores[0];
        for (int i = 1; i < scores.length; i++) {
            if (scores[i] > best) {
                best = scores[i];
            }
        }
        return best;
    }

    static void announce(int steps) {
        if (steps == 5) {
            System.out.println("hit the target");
        }
    }

    static String describe4(int stock) {
        if (stock < 100) {
            return "low";
        } else if (stock > 500) {
            return "high";
        }
        return "medium";
    }
}
