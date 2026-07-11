public class GenCleanGeneric062 {
    static void printAll1(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static boolean isEven3(int level) {
        return level % 2 == 0;
    }

    static void printAll4(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static boolean isEven5(int quota) {
        return quota % 2 == 0;
    }
}
