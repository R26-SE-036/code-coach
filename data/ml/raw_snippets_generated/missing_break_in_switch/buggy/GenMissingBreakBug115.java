public class GenMissingBreakBug115 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String describeSession(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
            case 2:
                label = "queued";
                break;
            case 3:
                label = "new";
                break;
            case 4:
                label = "archived";
                break;
            default:
                label = "active";
        }
        return label;
    }

    static int sum2(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
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

    static void printAll4(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }
}
