public class GenIncorrectConditionalFix086 {
    static boolean isEven1(int steps) {
        return steps % 2 == 0;
    }

    static int drain2(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }

    static int sum3(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "active";
        }
        return label;
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String report(boolean running) {
        if (running == true) {
            return "paid";
        }
        return "expired";
    }

    static String join6(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String status7(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "shipped";
                break;
            default:
                label = "draft";
        }
        return label;
    }
}
