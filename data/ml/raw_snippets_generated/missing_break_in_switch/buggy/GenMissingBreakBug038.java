public class GenMissingBreakBug038 {
    static String describe1(int stock) {
        if (stock < 100) {
            return "low";
        } else if (stock > 500) {
            return "high";
        }
        return "medium";
    }

    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
            case 2:
                label = "draft";
                break;
            case 3:
                label = "archived";
                break;
            case 4:
                label = "closed";
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

    static boolean isEven3(int steps) {
        return steps % 2 == 0;
    }

    static int average4(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static boolean isEven5(int total) {
        return total % 2 == 0;
    }
}
