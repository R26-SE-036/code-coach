public class GenOffByOneBug030 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static String describe2(int attempts) {
        if (attempts < 10) {
            return "low";
        } else if (attempts > 50) {
            return "high";
        }
        return "medium";
    }

    static int countAbove(int[] ratings, int threshold) {
        int hits = 0;
        for (int i = 0; i <= ratings.length; i++) {
            if (ratings[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }

    static int sum3(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
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
                label = "new";
                break;
            case 2:
                label = "active";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}
