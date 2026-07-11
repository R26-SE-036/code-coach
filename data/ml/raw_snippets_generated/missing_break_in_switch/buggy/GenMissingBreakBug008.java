public class GenMissingBreakBug008 {
    static int sum1(int[] sizes) {
        int total = 0;
        for (int i = 0; i < sizes.length; i++) {
            total += sizes[i];
        }
        return total;
    }

    static String describeBatch(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "active";
            case 3:
                label = "paid";
                break;
            default:
                label = "closed";
        }
        return label;
    }

    static boolean isEven2(int quota) {
        return quota % 2 == 0;
    }

    static String describe3(int steps) {
        if (steps < 5) {
            return "low";
        } else if (steps > 20) {
            return "high";
        }
        return "medium";
    }

    static int largest4(int[] ages) {
        int best = ages[0];
        for (int i = 1; i < ages.length; i++) {
            if (ages[i] > best) {
                best = ages[i];
            }
        }
        return best;
    }

    static String join5(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
