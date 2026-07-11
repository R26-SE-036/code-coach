public class GenCleanFallThrough010 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
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

    static boolean isEven2(int attempts) {
        return attempts % 2 == 0;
    }
}
