public class GenCleanScannerLoop002 {
    static void printAll1(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static int drain3(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }

    static void readAll(java.util.Scanner scanner) {
        while (scanner.hasNextLine()) {
            System.out.println(scanner.nextLine());
        }
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
