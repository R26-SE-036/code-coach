public class GenArrayIndexBug039 {
    static String describe1(int stock) {
        if (stock < 10) {
            return "low";
        } else if (stock > 50) {
            return "high";
        }
        return "medium";
    }

    static void stampLast(int[] prices, int value) {
        prices[prices.length] = value;
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describe3(int total) {
        if (total < 100) {
            return "low";
        } else if (total > 500) {
            return "high";
        }
        return "medium";
    }

    static boolean isEven4(int total) {
        return total % 2 == 0;
    }

    static String status5(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "paid";
        }
        return label;
    }
}
