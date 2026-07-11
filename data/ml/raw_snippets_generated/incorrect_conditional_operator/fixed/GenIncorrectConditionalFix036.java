public class GenIncorrectConditionalFix036 {
    static int largest1(int[] values) {
        int best = values[0];
        for (int i = 1; i < values.length; i++) {
            if (values[i] > best) {
                best = values[i];
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

    static String report(boolean valid) {
        if (valid == true) {
            return "closed";
        }
        return "archived";
    }
}
