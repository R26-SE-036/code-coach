public class GenMissingBreakBug102 {
    static String describe1(int level) {
        if (level < 5) {
            return "low";
        } else if (level > 20) {
            return "high";
        }
        return "medium";
    }

    static String describeItem(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
            case 2:
                label = "closed";
                break;
            case 3:
                label = "expired";
                break;
            case 4:
                label = "final";
                break;
            default:
                label = "archived";
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

    static void printAll3(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static int drain4(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static int sum5(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }
}
