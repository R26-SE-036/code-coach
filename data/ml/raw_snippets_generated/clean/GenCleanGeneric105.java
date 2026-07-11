public class GenCleanGeneric105 {
    static int drain1(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }

    static String describe2(int total) {
        if (total < 100) {
            return "low";
        } else if (total > 500) {
            return "high";
        }
        return "medium";
    }

    static String describe3(int attempts) {
        if (attempts < 100) {
            return "low";
        } else if (attempts > 500) {
            return "high";
        }
        return "medium";
    }

    static int sum4(int[] sizes) {
        int total = 0;
        for (int i = 0; i < sizes.length; i++) {
            total += sizes[i];
        }
        return total;
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String join6(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
