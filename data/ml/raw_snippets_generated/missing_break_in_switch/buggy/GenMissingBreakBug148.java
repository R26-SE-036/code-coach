public class GenMissingBreakBug148 {
    static int largest1(int[] marks) {
        int best = marks[0];
        for (int i = 1; i < marks.length; i++) {
            if (marks[i] > best) {
                best = marks[i];
            }
        }
        return best;
    }

    static boolean isEven2(int attempts) {
        return attempts % 2 == 0;
    }

    static String describeBatch(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "active";
                break;
            case 3:
                label = "final";
            case 4:
                label = "shipped";
                break;
            case 5:
                label = "paid";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int average4(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
