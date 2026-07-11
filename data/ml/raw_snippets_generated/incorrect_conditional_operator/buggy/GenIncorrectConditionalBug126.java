public class GenIncorrectConditionalBug126 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void printAll2(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "shipped";
                break;
            default:
                label = "closed";
        }
        return label;
    }

    static boolean matches(boolean open, boolean done) {
        if (open = done) {
            return true;
        }
        return false;
    }

    static String describe4(int quota) {
        if (quota < 100) {
            return "low";
        } else if (quota > 500) {
            return "high";
        }
        return "medium";
    }

    static void printAll5(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }
}
