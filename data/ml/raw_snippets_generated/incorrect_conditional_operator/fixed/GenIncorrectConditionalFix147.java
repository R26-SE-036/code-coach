public class GenIncorrectConditionalFix147 {
    static void printAll1(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static int sum2(int[] weights) {
        int total = 0;
        for (int i = 0; i < weights.length; i++) {
            total += weights[i];
        }
        return total;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "shipped";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static String join4(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String status5(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static String report(boolean active) {
        if (active == true) {
            return "expired";
        }
        return "paid";
    }
}
