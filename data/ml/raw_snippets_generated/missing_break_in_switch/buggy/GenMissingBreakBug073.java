public class GenMissingBreakBug073 {
    static String describe1(int budget) {
        if (budget < 100) {
            return "low";
        } else if (budget > 500) {
            return "high";
        }
        return "medium";
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describeBatch(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
            case 2:
                label = "closed";
                break;
            case 3:
                label = "draft";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static boolean isEven3(int level) {
        return level % 2 == 0;
    }

    static int average4(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
