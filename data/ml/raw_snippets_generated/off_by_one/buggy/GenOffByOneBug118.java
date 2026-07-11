public class GenOffByOneBug118 {
    static int largest1(int[] values) {
        int best = values[0];
        for (int i = 1; i < values.length; i++) {
            if (values[i] > best) {
                best = values[i];
            }
        }
        return best;
    }

    static int[] duplicate(int[] values) {
        int[] copy = new int[values.length];
        for (int i = 0; i <= values.length; i++) {
            copy[i] = values[i];
        }
        return copy;
    }

    static String describe2(int stock) {
        if (stock < 100) {
            return "low";
        } else if (stock > 500) {
            return "high";
        }
        return "medium";
    }
}
