public class GenOffByOneFix026 {
    static boolean isEven1(int total) {
        return total % 2 == 0;
    }

    static int sum2(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "new";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static String describe5(int budget) {
        if (budget < 100) {
            return "low";
        } else if (budget > 500) {
            return "high";
        }
        return "medium";
    }

    static int[] duplicate(int[] values) {
        int[] copy = new int[values.length];
        for (int i = 0; i < values.length; i++) {
            copy[i] = values[i];
        }
        return copy;
    }
}
