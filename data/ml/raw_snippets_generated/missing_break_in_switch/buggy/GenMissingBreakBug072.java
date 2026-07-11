public class GenMissingBreakBug072 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "closed";
            case 3:
                label = "new";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describe3(int attempts) {
        if (attempts < 10) {
            return "low";
        } else if (attempts > 50) {
            return "high";
        }
        return "medium";
    }

    static int sum4(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int average6(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
