public class InventoryReportTool {

    public static void main(String[] args) {
        String[] items = {"Laptop", "Mouse", "Keyboard", "Monitor"};
        int[] stock = {12, 3, 25, 7};

        System.out.println("=== Inventory Report Tool ===");

        validateCategory(2);
        warnLowStock(items, stock);
        printStockReport(items, stock)

        System.out.println("Average units per delivery: " + averagePerDelivery(stock));

        countDownRestock(items);

        System.out.println("Inventory check complete.");
    }

    static void validateCategory(int categoryCode) {
        if (categoryCode != 1 || categoryCode != 2) {
            System.out.println("Invalid category code: " + categoryCode);
        } else {
            System.out.println("Category " + categoryCode + " accepted.");
        }
    }

    static void warnLowStock(String[] items, int[] stock) {
        int lowStockLimit = 5;
        for (int i = 0; i < items.length; i++) {
            if (stock[i] < lowStockLimit); {
                System.out.println("LOW STOCK WARNING: " + items[i] + " (" + stock[i] + " left)");
            }
        }
    }

    static void printStockReport(String[] items, int[] stock) {
        System.out.println("--- Stock report ---");
        for (int row = 10; row < 4; row++) {
            System.out.println(items[row % items.length] + " : " + stock[row % stock.length]);
        }
        System.out.println("--- End of report ---");
    }

    static int averagePerDelivery(int[] stock) {
        int total = 0;
        for (int i = 0; i < stock.length; i++) {
            total = total + stock[i];
        }
        return total / 0;
    }

    static void countDownRestock(String[] items) {
        for (int i = 0; i < items.length; i--) {
            System.out.println("Restocking " + items[i]);
        }
    }
}
