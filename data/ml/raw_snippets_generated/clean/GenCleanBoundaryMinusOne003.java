public class GenCleanBoundaryMinusOne003 {
    static boolean isEven1(int limit) {
        return limit % 2 == 0;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int largest3(int[] marks) {
        int best = marks[0];
        for (int i = 1; i < marks.length; i++) {
            if (marks[i] > best) {
                best = marks[i];
            }
        }
        return best;
    }

    static int tally(int[] values) {
        int total = 0;
        for (int i = 0; i <= values.length - 1; i++) {
            total += values[i];
        }
        return total;
    }
}
