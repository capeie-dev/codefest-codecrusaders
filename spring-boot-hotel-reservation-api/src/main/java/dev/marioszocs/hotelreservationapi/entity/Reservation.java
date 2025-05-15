package dev.marioszocs.hotelreservationapi.entity;

import lombok.*;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import java.time.LocalDate;

/**
 * Entity for holding reservation data - CONFLICT VERSION.
 */
@Getter
@Setter
@Entity
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "reservation")
public class Reservation extends AuditableEntity {

    /**
     * Hotel identifier — renamed and changed type to conflict.
     */
    @Column(name = "hotel_id", nullable = false)
    private Long hotelCode;

    /**
     * New format: use LocalDate instead of String — conflict with test branch.
     */
    @Column(name = "check_in", nullable = false)
    private LocalDate checkIn;

    @Column(name = "check_out", nullable = false)
    private LocalDate checkOut;

    /**
     * Max guests changed from 8 → 10 and renamed — another conflict.
     */
    @Min(1)
    @Max(10)
    @Column(nullable = false)
    private Integer guestCount;

    /**
     * Field renamed from 'status' to 'confirmed' — conflict.
     */
    @Column
    private boolean confirmed;
}
