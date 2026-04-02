public class ArrayIndexBug014 {
    public int fetchBonus(int[] bonuses) {
        return bonuses[bonuses.length] + 5;
    }
}