public class GenMissingBreakBug035 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "active";
                break;
            case 3:
                label = "final";
            case 4:
                label = "expired";
                break;
            default:
                label = "archived";
        }
        return label;
    }

    static String describe2(int stock) {
        if (stock < 5) {
            return "low";
        } else if (stock > 20) {
            return "high";
        }
        return "medium";
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String describe4(int level) {
        if (level < 100) {
            return "low";
        } else if (level > 500) {
            return "high";
        }
        return "medium";
    }

    static void printAll5(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }

    static int sum6(int[] totals) {
        int total = 0;
        for (int i = 0; i < totals.length; i++) {
            total += totals[i];
        }
        return total;
    }

    static void printAll7(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }
}
