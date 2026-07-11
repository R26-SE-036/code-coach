public class GenCleanFallThrough030 {
    static int sum1(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }

    static void printAll2(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static void printPermissions(int level) {
        switch (level) {
            case 3:
                System.out.println("can delete");
                // fall through: higher levels include lower rights
            case 2:
                System.out.println("can edit");
                // fall through
            case 1:
                System.out.println("can view");
                break;
            default:
                System.out.println("no access");
        }
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static void printAll4(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static int largest5(int[] ratings) {
        int best = ratings[0];
        for (int i = 1; i < ratings.length; i++) {
            if (ratings[i] > best) {
                best = ratings[i];
            }
        }
        return best;
    }
}
