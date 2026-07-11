public class GenCleanGeneric028 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
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

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int drain4(int level) {
        int handled = 0;
        while (level > 0) {
            handled += level;
            level--;
        }
        return handled;
    }

    static String describe5(int limit) {
        if (limit < 5) {
            return "low";
        } else if (limit > 20) {
            return "high";
        }
        return "medium";
    }

    static int largest6(int[] sizes) {
        int best = sizes[0];
        for (int i = 1; i < sizes.length; i++) {
            if (sizes[i] > best) {
                best = sizes[i];
            }
        }
        return best;
    }
}
