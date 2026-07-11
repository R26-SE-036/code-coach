public class GenArrayIndexBug161 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void printAll2(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void printAll4(int[] ages) {
        for (int value : ages) {
            System.out.println(value);
        }
    }

    static String status5(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "closed";
        }
        return label;
    }

    static int lastOf(int[] scores) {
        return scores[scores.length];
    }
}
