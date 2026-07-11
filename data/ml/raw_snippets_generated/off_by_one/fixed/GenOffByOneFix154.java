public class GenOffByOneFix154 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describe2(int total) {
        if (total < 100) {
            return "low";
        } else if (total > 500) {
            return "high";
        }
        return "medium";
    }

    static int sum3(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }

    static int countAbove(int[] ages, int threshold) {
        int hits = 0;
        for (int i = 0; i < ages.length; i++) {
            if (ages[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }

    static void printAll4(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }
}
