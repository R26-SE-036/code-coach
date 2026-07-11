public class GenWhileNoUpdateFix018 {
    static String describe1(int steps) {
        if (steps < 100) {
            return "low";
        } else if (steps > 500) {
            return "high";
        }
        return "medium";
    }

    static int largest2(int[] values) {
        int best = values[0];
        for (int i = 1; i < values.length; i++) {
            if (values[i] > best) {
                best = values[i];
            }
        }
        return best;
    }

    static void countdown(int total) {
        while (total > 0) {
            System.out.println("left: " + total);
            total--;
        }
    }
}
