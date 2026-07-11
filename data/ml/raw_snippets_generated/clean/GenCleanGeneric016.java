public class GenCleanGeneric016 {
    static void printAll1(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "draft";
                break;
            default:
                label = "closed";
        }
        return label;
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String join4(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int drain5(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }
}
