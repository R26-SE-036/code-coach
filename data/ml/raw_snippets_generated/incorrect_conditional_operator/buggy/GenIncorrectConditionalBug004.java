public class GenIncorrectConditionalBug004 {
    static String report(boolean done) {
        if (done = true) {
            return "active";
        }
        return "archived";
    }

    static int largest1(int[] sizes) {
        int best = sizes[0];
        for (int i = 1; i < sizes.length; i++) {
            if (sizes[i] > best) {
                best = sizes[i];
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
}
